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