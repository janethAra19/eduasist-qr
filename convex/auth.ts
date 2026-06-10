import { ConvexError } from "convex/values";
import { QueryCtx, MutationCtx } from "./_generated/server";

export async function requireSession(
  ctx: QueryCtx | MutationCtx,
  tokenHash: string,
) {
  const session = await ctx.db
    .query("sessions")
    .withIndex("by_token_hash", (q) => q.eq("tokenHash", tokenHash))
    .unique();

  if (!session || !session.isActive) throw new ConvexError("Sesión inválida");
  if (session.expiresAt < Date.now()) throw new ConvexError("Sesión expirada");

  const user = await ctx.db.get(session.userId);
  if (!user || !user.isActive) throw new ConvexError("Usuario inactivo");

  return { session, user, schoolId: session.schoolId, userId: session.userId, role: session.role };
}

export function requireRole(auth: { role: string }, allowedRoles: string[]) {
  if (!allowedRoles.includes(auth.role)) throw new ConvexError("Permiso denegado");
}