import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

// Listar alumnos por escuela
export const listBySchool = query({
  args: { schoolId: v.id("schools") },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("students")
      .withIndex("by_school", (q) => q.eq("schoolId", args.schoolId))
      .filter((q) => q.eq(q.field("status"), "active"))
      .collect();
  },
});

// Crear alumno
export const create = mutation({
  args: {
    schoolId: v.id("schools"),
    studentCode: v.string(),
    name: v.string(),
    grade: v.string(),
    group: v.string(),
    photoUrl: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const now = Date.now();
    return await ctx.db.insert("students", {
      ...args,
      status: "active",
      createdAt: now,
      updatedAt: now,
    });
  },
});