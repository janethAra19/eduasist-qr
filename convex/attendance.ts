import { query, mutation } from "./_generated/server";
import { v } from "convex/values";
import { requireSession, requireRole } from "./auth";

export const getByDate = query({
  args: {
    tokenHash: v.string(),
    date: v.string(),
  },
  handler: async (ctx, args) => {
    const auth = await requireSession(ctx, args.tokenHash);
    requireRole(auth, ["admin", "prefect"]);

    const records = await ctx.db
      .query("attendance")
      .withIndex("by_school_date", (q) =>
        q.eq("schoolId", auth.schoolId).eq("attendanceDate", args.date)
      )
      .collect();

    const result = [];
    for (const r of records) {
      const student = await ctx.db.get(r.studentId);
      result.push({
        ...r,
        studentName: student?.name ?? "Desconocido",
        studentGrade: student?.grade ?? "",
        studentGroup: student?.group ?? "",
      });
    }
    return result;
  },
});

export const getTodaySummary = query({
  args: { tokenHash: v.string() },
  handler: async (ctx, args) => {
    const auth = await requireSession(ctx, args.tokenHash);
    requireRole(auth, ["admin", "prefect"]);

    const today = new Date().toISOString().slice(0, 10);

    const present = await ctx.db
      .query("attendance")
      .withIndex("by_school_date", (q) =>
        q.eq("schoolId", auth.schoolId).eq("attendanceDate", today)
      )
      .filter((q) => q.eq(q.field("status"), "present"))
      .collect();

    const allStudents = await ctx.db
      .query("students")
      .withIndex("by_school", (q) => q.eq("schoolId", auth.schoolId))
      .filter((q) => q.eq(q.field("status"), "active"))
      .collect();

    return {
      present: present.length,
      absent: allStudents.length - present.length,
      total: allStudents.length,
    };
  },
});

// ── NUEVO: registrar asistencia escaneando el QR del alumno ──────────────────
export const registerByQr = mutation({
  args: {
    sessionTokenHash: v.string(),
    qrTokenHash: v.string(),
  },
  handler: async (ctx, args) => {
    const auth = await requireSession(ctx, args.sessionTokenHash);
    requireRole(auth, ["admin", "prefect"]);

    // Buscar el QR
    const qr = await ctx.db
      .query("qrTokens")
      .withIndex("by_token_hash", (q) => q.eq("tokenHash", args.qrTokenHash))
      .filter((q) => q.eq(q.field("status"), "active"))
      .first();

    if (!qr) throw new Error("QR inválido o no encontrado");

    const today = new Date().toISOString().slice(0, 10);

    // Verificar si ya fue registrado hoy
    const existing = await ctx.db
      .query("attendance")
      .withIndex("by_student_date", (q) =>
        q.eq("studentId", qr.studentId).eq("attendanceDate", today)
      )
      .first();

    if (existing) {
      const student = await ctx.db.get(qr.studentId);
      return { alreadyRegistered: true, studentName: student?.name ?? "" };
    }

    const now = Date.now();
    await ctx.db.insert("attendance", {
      schoolId: auth.schoolId,
      studentId: qr.studentId,
      scannedByUserId: auth.userId,
      scannedAt: now,
      attendanceDate: today,
      status: "present",
      notificationStatus: "pending",
      createdAt: now,
    });

    const student = await ctx.db.get(qr.studentId);
    return {
      alreadyRegistered: false,
      studentName:  student?.name  ?? "",
      studentGrade: student?.grade ?? "",
      studentGroup: student?.group ?? "",
      studentId:    qr.studentId,
      attendanceId: await ctx.db
        .query("attendance")
        .withIndex("by_student_date", (q) =>
          q.eq("studentId", qr.studentId).eq("attendanceDate", today)
        )
        .first()
        .then((r) => r?._id ?? null),
    };
  },
});
// ── Marca el status de notificación (usado desde la action) ──────────────────
export const markNotified = mutation({
  args: {
    attendanceId: v.id("attendance"),
    status: v.union(v.literal("sent"), v.literal("failed")),
  },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.attendanceId, {
      notificationStatus: args.status,
    });
    return { ok: true };
  },
});
