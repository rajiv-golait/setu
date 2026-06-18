/** Supabase app_metadata.role values used across the app. */
export type UserRole = "patient" | "provider" | "health_worker" | "admin";

export function roleFromMetadata(
  meta: Record<string, unknown> | undefined,
  email?: string | null,
): UserRole {
  const role = meta?.role;
  if (role === "provider" || role === "health_worker" || role === "admin") {
    return role;
  }
  const devAdmin = process.env.NEXT_PUBLIC_DEV_ADMIN_EMAIL?.trim().toLowerCase();
  if (devAdmin && email?.trim().toLowerCase() === devAdmin) {
    return "admin";
  }
  return "patient";
}

export function homeForRole(role: UserRole): string {
  switch (role) {
    case "provider":
      return "/doctor";
    case "health_worker":
      return "/worker";
    case "admin":
      return "/admin";
    default:
      return "/";
  }
}

export function isRoleAllowedOnPath(role: UserRole, pathname: string): boolean {
  if (pathname.startsWith("/doctor/login")) return true;
  if (pathname.startsWith("/doctor")) return role === "provider" || role === "admin";
  if (pathname.startsWith("/worker")) return role === "health_worker" || role === "admin";
  if (pathname.startsWith("/admin")) return role === "admin";
  if (pathname.startsWith("/login") || pathname.startsWith("/onboarding")) return true;
  if (pathname.startsWith("/brief/") || pathname.startsWith("/share/")) return true;
  // Patient app routes — providers/workers redirected at middleware
  if (role === "provider" || role === "health_worker" || role === "admin") return false;
  return true;
}
