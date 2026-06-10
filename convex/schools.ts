import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

// Crear escuela inicial
export const create = mutation({
  args: {
    name: v.string(),
    code: v.string(),
    timezone: v.string(),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("schools")
      .withIndex("by_code", (q) => q.eq("code", args.code))
      .first();

    if (existing) return existing._id;

    const now = Date.now();
    return await ctx.db.insert("schools", {
      ...args,
      isActive: true,
      createdAt: now,
      updatedAt: now,
    });
  },
});

// Obtener escuela por código
export const getByCode = query({
  args: { code: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("schools")
      .withIndex("by_code", (q) => q.eq("code", args.code))
      .first();
  },
});