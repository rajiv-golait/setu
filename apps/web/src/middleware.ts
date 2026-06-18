import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

const PUBLIC_PREFIXES = [
  "/login",
  "/doctor/login",
  "/admin/login",
  "/doctor/pending",
  "/onboarding",
  "/brief/",
  "/share/",
];

function isPublicPath(pathname: string): boolean {
  return PUBLIC_PREFIXES.some((p) => pathname.startsWith(p));
}

function isDoctorAppPath(pathname: string): boolean {
  return pathname.startsWith("/doctor") && !pathname.startsWith("/doctor/login");
}

type UserRole = "patient" | "provider" | "health_worker" | "admin";

function roleFromMeta(
  meta: Record<string, unknown> | undefined,
  email?: string | null,
): UserRole {
  const r = meta?.role;
  if (r === "provider" || r === "health_worker" || r === "admin") return r;
  const devAdmin = process.env.NEXT_PUBLIC_DEV_ADMIN_EMAIL?.trim().toLowerCase();
  if (devAdmin && email?.trim().toLowerCase() === devAdmin) return "admin";
  return "patient";
}

function homeForRole(role: UserRole): string {
  if (role === "provider") return "/doctor";
  if (role === "health_worker") return "/worker";
  if (role === "admin") return "/admin";
  return "/";
}

export async function middleware(request: NextRequest) {
  if (process.env.NEXT_PUBLIC_SUPABASE_ENABLED !== "true") {
    return NextResponse.next();
  }

  const { pathname } = request.nextUrl;
  if (pathname.startsWith("/api/v1")) {
    return NextResponse.next();
  }

  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) {
    return NextResponse.next();
  }

  let response = NextResponse.next({ request });

  const supabase = createServerClient(url, key, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet) {
        cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value));
        response = NextResponse.next({ request });
        cookiesToSet.forEach(({ name, value, options }) =>
          response.cookies.set(name, value, options),
        );
      },
    },
  });

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    if (isPublicPath(pathname)) {
      return response;
    }
    const loginUrl = request.nextUrl.clone();
    if (pathname.startsWith("/admin")) {
      loginUrl.pathname = "/admin/login";
    } else {
      loginUrl.pathname = isDoctorAppPath(pathname) ? "/doctor/login" : "/login";
    }
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  const role = roleFromMeta(
    user.app_metadata as Record<string, unknown> | undefined,
    user.email,
  );

  if (pathname === "/login" || pathname === "/doctor/login" || pathname === "/admin/login") {
    const dest = request.nextUrl.clone();
    dest.pathname = homeForRole(role);
    return NextResponse.redirect(dest);
  }

  if (isDoctorAppPath(pathname) && role !== "provider" && role !== "admin") {
    const dest = request.nextUrl.clone();
    dest.pathname = homeForRole(role);
    return NextResponse.redirect(dest);
  }
  if (pathname.startsWith("/worker") && role !== "health_worker" && role !== "admin") {
    const dest = request.nextUrl.clone();
    dest.pathname = homeForRole(role);
    return NextResponse.redirect(dest);
  }
  if (pathname.startsWith("/admin") && role !== "admin") {
    const dest = request.nextUrl.clone();
    dest.pathname = homeForRole(role);
    return NextResponse.redirect(dest);
  }
  if (
    role === "provider" &&
    !pathname.startsWith("/doctor") &&
    !pathname.startsWith("/brief/") &&
    !pathname.startsWith("/share/")
  ) {
    const dest = request.nextUrl.clone();
    dest.pathname = "/doctor";
    return NextResponse.redirect(dest);
  }
  if (
    role === "health_worker" &&
    !pathname.startsWith("/worker") &&
    !pathname.startsWith("/brief/") &&
    !pathname.startsWith("/share/")
  ) {
    const dest = request.nextUrl.clone();
    dest.pathname = "/worker";
    return NextResponse.redirect(dest);
  }
  if (role === "admin" && pathname === "/") {
    const dest = request.nextUrl.clone();
    dest.pathname = "/admin";
    return NextResponse.redirect(dest);
  }

  return response;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|icon.svg).*)"],
};
