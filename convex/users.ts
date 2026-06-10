import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

// Crear usuario (admin o prefecto)
export const create = mutation({
  args: {
    schoolId: v.id("schools"),
    name: v.string(),
    email: v.string(),
    passwordHash: v.string(),
    role: v.union(v.literal("admin"), v.literal("prefect")),
  },
  handler: async (ctx, args) => {
    // Verificar si el email ya existe
    const existing = await ctx.db
      .query("users")
      .withIndex("by_email", (q) => q.eq("email", args.email))
      .first();

    if (existing) {
      throw new Error("El correo ya está registrado");
    }

    const now = Date.now();
    return await ctx.db.insert("users", {
      ...args,
      isActive: true,
      createdAt: now,
      updatedAt: now,
    });
  },
});

// Login — buscar usuario por email
export const getByEmail = query({
  args: { email: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("users")
      .withIndex("by_email", (q) => q.eq("email", args.email))
      .first();
  },
});