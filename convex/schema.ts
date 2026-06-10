import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  schools: defineTable({
    name: v.string(),
    code: v.string(),
    timezone: v.string(),
    isActive: v.boolean(),
    createdAt: v.number(),
    updatedAt: v.number(),
  }).index("by_code", ["code"]),

  users: defineTable({
    schoolId: v.id("schools"),
    name: v.string(),
    email: v.string(),
    passwordHash: v.string(),
    role: v.union(v.literal("admin"), v.literal("prefect")),
    isActive: v.boolean(),
    createdAt: v.number(),
    updatedAt: v.number(),
  })
    .index("by_school", ["schoolId"])
    .index("by_email", ["email"]),

  students: defineTable({
    schoolId: v.id("schools"),
    studentCode: v.string(),
    name: v.string(),
    grade: v.string(),
    group: v.string(),
    photoUrl: v.optional(v.string()),
    status: v.union(
      v.literal("active"),
      v.literal("inactive"),
      v.literal("graduated")
    ),
    createdAt: v.number(),
    updatedAt: v.number(),
  })
    .index("by_school", ["schoolId"])
    .index("by_school_grade_group", ["schoolId", "grade", "group"]),

  qrTokens: defineTable({
    schoolId: v.id("schools"),
    studentId: v.id("students"),
    tokenHash: v.string(),
    status: v.union(v.literal("active"), v.literal("revoked")),
    generatedAt: v.number(),
  })
    .index("by_token_hash", ["tokenHash"])
    .index("by_student_status", ["studentId", "status"]),

  attendance: defineTable({
    schoolId: v.id("schools"),
    studentId: v.id("students"),
    scannedByUserId: v.id("users"),
    scannedAt: v.number(),
    attendanceDate: v.string(),
    status: v.union(
      v.literal("present"),
      v.literal("late"),
      v.literal("absent")
    ),
    notificationStatus: v.union(
      v.literal("pending"),
      v.literal("sent"),
      v.literal("failed")
    ),
    createdAt: v.number(),
  })
    .index("by_school_date", ["schoolId", "attendanceDate"])
    .index("by_student_date", ["studentId", "attendanceDate"]),

  guardians: defineTable({
    schoolId: v.id("schools"),
    studentId: v.id("students"),
    name: v.string(),
    phone: v.string(),
    email: v.optional(v.string()),
    notifyWhatsApp: v.boolean(),
    notifyEmail: v.boolean(),
    isActive: v.boolean(),
    createdAt: v.number(),
  })
    .index("by_student", ["studentId"])
    .index("by_school", ["schoolId"]),
});