import { mutation } from "./_generated/server";
import { v } from "convex/values";
import { requireSession } from "./auth";

export const create = mutation({
  args: {
    userId: v.id("users"),
    schoolId: v.id("schools"),
    role: v.union(v.literal("admin"), v.literal("prefect")),
    tokenHash: v.string(),
  },
  handler: async (ctx, args) => {
    const now = Date.now();
    return await ctx.db.insert("sessions", {
      ...args,
      isActive: true,
      createdAt: now,
      expiresAt: now + 8 * 60 * 60 * 1000,
    });
  },
});

export const logout = mutation({
  args: { tokenHash: v.string() },
  handler: async (ctx, args) => {
    const auth = await requireSession(ctx, args.tokenHash);
    await ctx.db.patch(auth.session._id, { isActive: false });
    return { ok: true };
  },
});