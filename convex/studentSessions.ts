import { mutation } from "./_generated/server";
import { v } from "convex/values";

export const create = mutation({
  args: {
    studentId: v.id("students"),
    schoolId: v.id("schools"),
    tokenHash: v.string(),
  },
  handler: async (ctx, args) => {
    const now = Date.now();
    return await ctx.db.insert("studentSessions", {
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
    const session = await ctx.db
      .query("studentSessions")
      .withIndex("by_token_hash", (q) => q.eq("tokenHash", args.tokenHash))
      .first();
    if (session) await ctx.db.patch(session._id, { isActive: false });
    return { ok: true };
  },
});
