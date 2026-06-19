import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

// ── Registro libre — crea escuela automática si no existe ────────────────────
export const register = mutation({
  args: {
    name: v.string(),
    email: v.string(),
    passwordHash: v.string(),
    role: v.union(v.literal("admin"), v.literal("prefect")),
    schoolName: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    // Verificar email duplicado
    const existing = await ctx.db
      .query("users")
      .withIndex("by_email", (q) => q.eq("email", args.email))
      .first();
    if (existing) throw new Error("Este correo ya está registrado");

    const now = Date.now();

    // Buscar o crear escuela por defecto
    const schoolName = args.schoolName?.trim() || "Mi Escuela";
    const schoolCode = schoolName
      .toUpperCase()
      .replace(/\s+/g, "")
      .slice(0, 8);

    let school = await ctx.db
      .query("schools")
      .withIndex("by_code", (q) => q.eq("code", schoolCode))
      .first();

    if (!school) {
      const schoolId = await ctx.db.insert("schools", {
        name: schoolName,
        code: schoolCode,
        timezone: "America/Mexico_City",
        isActive: true,
        createdAt: now,
        updatedAt: now,
      });
      school = await ctx.db.get(schoolId);
    }

    const userId = await ctx.db.insert("users", {
      schoolId: school!._id,
      name: args.name,
      email: args.email,
      passwordHash: args.passwordHash,
      role: args.role,
      isActive: true,
      createdAt: now,
      updatedAt: now,
    });

    return { userId, schoolId: school!._id };
  },
});

// ── Registro de ALUMNO — crea su propio registro + QR automáticamente ────────
export const registerStudent = mutation({
  args: {
    name: v.string(),
    email: v.string(),
    passwordHash: v.string(),
    grade: v.string(),
    group: v.string(),
    schoolName: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    // Verificar que el correo no esté ya usado por un alumno
    const existingStudents = await ctx.db.query("students").collect();
    const dup = existingStudents.find((s: any) => s.email === args.email);
    if (dup) throw new Error("Este correo ya está registrado como alumno");

    // También verificar que no choque con un admin/prefecto
    const existingUser = await ctx.db
      .query("users")
      .withIndex("by_email", (q) => q.eq("email", args.email))
      .first();
    if (existingUser) throw new Error("Este correo ya está registrado");

    const now = Date.now();

    // Buscar o crear escuela por defecto (igual que en register de staff)
    const schoolName = args.schoolName?.trim() || "Mi Escuela";
    const schoolCode = schoolName.toUpperCase().replace(/\s+/g, "").slice(0, 8);

    let school = await ctx.db
      .query("schools")
      .withIndex("by_code", (q) => q.eq("code", schoolCode))
      .first();

    if (!school) {
      const schoolId = await ctx.db.insert("schools", {
        name: schoolName,
        code: schoolCode,
        timezone: "America/Mexico_City",
        isActive: true,
        createdAt: now,
        updatedAt: now,
      });
      school = await ctx.db.get(schoolId);
    }

    // Generar código de alumno automático único: AL + timestamp corto
    const studentCode = "AL" + now.toString().slice(-8);

    // Crear el alumno
    const studentId = await ctx.db.insert("students", {
      schoolId: school!._id,
      studentCode,
      name: args.name,
      grade: args.grade,
      group: args.group,
      email: args.email,
      passwordHash: args.passwordHash,
      status: "active",
      createdAt: now,
      updatedAt: now,
    });

    // Generar su QR automáticamente
    const qrTokenHash = studentCode + "_" + now.toString();
    await ctx.db.insert("qrTokens", {
      schoolId: school!._id,
      studentId,
      tokenHash: qrTokenHash,
      status: "active",
      generatedAt: now,
    });

    return { studentId, schoolId: school!._id, studentCode };
  },
});

// ── Login alumno — buscar por email ──────────────────────────────────────────
export const getStudentByEmail = query({
  args: { email: v.string() },
  handler: async (ctx, args) => {
    const students = await ctx.db.query("students").collect();
    return students.find((s: any) => s.email === args.email) ?? null;
  },
});

// ── Login — buscar por email ─────────────────────────────────────────────────
export const getByEmail = query({
  args: { email: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("users")
      .withIndex("by_email", (q) => q.eq("email", args.email))
      .first();
  },
});

// ── Crear usuario (desde admin) ──────────────────────────────────────────────
export const create = mutation({
  args: {
    schoolId: v.id("schools"),
    name: v.string(),
    email: v.string(),
    passwordHash: v.string(),
    role: v.union(v.literal("admin"), v.literal("prefect")),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("users")
      .withIndex("by_email", (q) => q.eq("email", args.email))
      .first();
    if (existing) throw new Error("El correo ya está registrado");

    const now = Date.now();
    return await ctx.db.insert("users", {
      ...args,
      isActive: true,
      createdAt: now,
      updatedAt: now,
    });
  },
});

