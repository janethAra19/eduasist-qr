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
    // Generar QR token automáticamente
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

// ── NUEVO: obtener QR token de un alumno (para mostrarlo en admin) ────────────
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

// ── NUEVO: buscar alumno por su QR token (para el escáner del prefecto) ───────
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