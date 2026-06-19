import { mutation, query } from "./_generated/server";
import { v } from "convex/values";
import { requireSession, requireRole } from "./auth";

export const listBySchool = query({
  args: { tokenHash: v.string() },
  handler: async (ctx, args) => {
    const auth = await requireSession(ctx, args.tokenHash);
    requireRole(auth, ["admin", "prefect"]);
    return await ctx.db
      .query("students")
      .withIndex("by_school", (q) => q.eq("schoolId", auth.schoolId))
      .filter((q) => q.eq(q.field("status"), "active"))
      .collect();
  },
});

export const create = mutation({
  args: {
    tokenHash: v.string(),
    studentCode: v.string(),
    name: v.string(),
    grade: v.string(),
    group: v.string(),
  },
  handler: async (ctx, args) => {
    const auth = await requireSession(ctx, args.tokenHash);
    requireRole(auth, ["admin"]);
    const now = Date.now();
    const studentId = await ctx.db.insert("students", {
      schoolId: auth.schoolId,
      studentCode: args.studentCode,
      name: args.name,
      grade: args.grade,
      group: args.group,
      status: "active",
      createdAt: now,
      updatedAt: now,
    });
    const tokenHash = args.studentCode + "_" + now.toString();
    await ctx.db.insert("qrTokens", {
      schoolId: auth.schoolId,
      studentId: studentId,
      tokenHash: tokenHash,
      status: "active",
      generatedAt: now,
    });
    return studentId;
  },
});

export const deleteStudent = mutation({
  args: {
    tokenHash: v.string(),
    studentId: v.id("students"),
  },
  handler: async (ctx, args) => {
    const auth = await requireSession(ctx, args.tokenHash);
    requireRole(auth, ["admin"]);
    await ctx.db.patch(args.studentId, {
      status: "inactive",
      updatedAt: Date.now(),
    });
    return { ok: true };
  },
});

export const generateUploadUrl = mutation({
  args: { tokenHash: v.string() },
  handler: async (ctx, args) => {
    const auth = await requireSession(ctx, args.tokenHash);
    requireRole(auth, ["admin"]);
    return await ctx.storage.generateUploadUrl();
  },
});

export const updatePhoto = mutation({
  args: {
    tokenHash: v.string(),
    studentId: v.id("students"),
    storageId: v.string(),
  },
  handler: async (ctx, args) => {
    const auth = await requireSession(ctx, args.tokenHash);
    requireRole(auth, ["admin"]);
    const url = await ctx.storage.getUrl(args.storageId as any);
    await ctx.db.patch(args.studentId, {
      photoUrl: url ?? undefined,
      updatedAt: Date.now(),
    });
    return { ok: true };
  },
});

export const removePhoto = mutation({
  args: {
    tokenHash: v.string(),
    studentId: v.id("students"),
  },
  handler: async (ctx, args) => {
    const auth = await requireSession(ctx, args.tokenHash);
    requireRole(auth, ["admin"]);
    await ctx.db.patch(args.studentId, {
      photoUrl: undefined,
      updatedAt: Date.now(),
    });
    return { ok: true };
  },
});

export const getQrToken = query({
  args: {
    tokenHash: v.string(),
    studentId: v.id("students"),
  },
  handler: async (ctx, args) => {
    const auth = await requireSession(ctx, args.tokenHash);
    requireRole(auth, ["admin"]);
    const qr = await ctx.db
      .query("qrTokens")
      .withIndex("by_student_status", (q) =>
        q.eq("studentId", args.studentId).eq("status", "active")
      )
      .first();
    return qr ? qr.tokenHash : null;
  },
});

export const getByQrToken = query({
  args: {
    qrTokenHash: v.string(),
    sessionTokenHash: v.string(),
  },
  handler: async (ctx, args) => {
    const auth = await requireSession(ctx, args.sessionTokenHash);
    requireRole(auth, ["admin", "prefect"]);
    const qr = await ctx.db
      .query("qrTokens")
      .withIndex("by_token_hash", (q) => q.eq("tokenHash", args.qrTokenHash))
      .filter((q) => q.eq(q.field("status"), "active"))
      .first();
    if (!qr) return null;
    const student = await ctx.db.get(qr.studentId);
    return student ?? null;
  },
});

export const getWithQR = query({
  args: { tokenHash: v.string() },
  handler: async (ctx, args) => {
    const auth = await requireSession(ctx, args.tokenHash);
    requireRole(auth, ["admin"]);
    const students = await ctx.db
      .query("students")
      .withIndex("by_school", (q) => q.eq("schoolId", auth.schoolId))
      .filter((q) => q.eq(q.field("status"), "active"))
      .collect();
    const result = [];
    for (const s of students) {
      const qr = await ctx.db
        .query("qrTokens")
        .withIndex("by_student_status", (q) =>
          q.eq("studentId", s._id).eq("status", "active")
        )
        .first();
      result.push({
        ...s,
        qrToken: qr?.tokenHash ?? null,
      });
    }
    return result;
  },
});

export const getMyProfile = query({
  args: {
    studentCode: v.string(),
    schoolCode: v.string(),
  },
  handler: async (ctx, args) => {
    const school = await ctx.db
      .query("schools")
      .withIndex("by_code", (q) => q.eq("code", args.schoolCode))
      .first();

    if (!school) throw new Error("Escuela no encontrada");

    const students = await ctx.db
      .query("students")
      .withIndex("by_school", (q) => q.eq("schoolId", school._id))
      .filter((q) => q.eq(q.field("studentCode"), args.studentCode))
      .collect();

    const student = students[0];
    if (!student) throw new Error("Alumno no encontrado");

    const qr = await ctx.db
      .query("qrTokens")
      .withIndex("by_student_status", (q) =>
        q.eq("studentId", student._id).eq("status", "active")
      )
      .first();

    return {
      ...student,
      qrToken: qr?.tokenHash ?? null,
    };
  },
});
// ── Auto-registro del alumno (sin sesión) ─────────────────────────────────────
// El alumno llena nombre, grado, grupo y código de escuela.
// Se crea el estudiante + QR automáticamente y aparece en el admin al instante.
export const selfRegister = mutation({
  args: {
    schoolCode:  v.string(),
    name:        v.string(),
    grade:       v.string(),
    group:       v.string(),
    studentCode: v.optional(v.string()), // si lo deja vacío se genera automático
  },
  handler: async (ctx, args) => {
    // Buscar la escuela
    const school = await ctx.db
      .query("schools")
      .withIndex("by_code", (q) => q.eq("code", args.schoolCode.toUpperCase()))
      .first();
    if (!school) throw new Error("Código de escuela no encontrado. Pídelo a tu administrador.");

    const now = Date.now();

    // Generar código único si no se proporcionó
    const studentCode = args.studentCode?.trim().toUpperCase() ||
      args.schoolCode.toUpperCase() + "-" + now.toString().slice(-5);

    // Verificar que el código no esté duplicado en esa escuela
    const existing = await ctx.db
      .query("students")
      .withIndex("by_school", (q) => q.eq("schoolId", school._id))
      .filter((q) => q.eq(q.field("studentCode"), studentCode))
      .first();
    if (existing) throw new Error("Ese código de alumno ya está registrado en esta escuela.");

    // Crear alumno
    const studentId = await ctx.db.insert("students", {
      schoolId:    school._id,
      studentCode: studentCode,
      name:        args.name,
      grade:       args.grade,
      group:       args.group,
      status:      "active",
      createdAt:   now,
      updatedAt:   now,
    });

    // Crear QR automáticamente
    const tokenHash = studentCode + "_" + now.toString();
    await ctx.db.insert("qrTokens", {
      schoolId:    school._id,
      studentId:   studentId,
      tokenHash:   tokenHash,
      status:      "active",
      generatedAt: now,
    });

    return {
      studentId,
      studentCode,
      qrToken: tokenHash,
      name:    args.name,
      grade:   args.grade,
      group:   args.group,
    };
  },
});