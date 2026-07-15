import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().min(1, "Email is required").email("Enter a valid email address."),
  password: z.string().min(1, "Password is required."),
});
export type LoginFormValues = z.infer<typeof loginSchema>;

const COMMON_WEAK_PASSWORDS = new Set([
  "password", "password1", "password123", "12345678", "123456789", "qwerty123",
  "letmein1", "welcome1", "admin123", "iloveyou", "monkey123", "football1",
  "abc12345", "changeme", "passw0rd", "trustno1", "sunshine1", "princess1",
]);

export interface PasswordRule {
  key: string;
  label: string;
  test: (password: string) => boolean;
}

export const PASSWORD_RULES: PasswordRule[] = [
  { key: "length", label: "At least 8 characters", test: (p) => p.length >= 8 },
  { key: "upper", label: "One uppercase letter", test: (p) => /[A-Z]/.test(p) },
  { key: "lower", label: "One lowercase letter", test: (p) => /[a-z]/.test(p) },
  { key: "number", label: "One number", test: (p) => /\d/.test(p) },
  { key: "special", label: "One special character", test: (p) => /[^A-Za-z0-9]/.test(p) },
];

export function passwordStrengthScore(password: string): number {
  return PASSWORD_RULES.filter((rule) => rule.test(password)).length;
}

export const registerSchema = z
  .object({
    first_name: z.string().min(1, "First name is required.").max(120),
    last_name: z.string().max(120).optional().default(""),
    email: z.string().min(1, "Email is required").email("Enter a valid email address."),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters.")
      .max(128, "Password is too long.")
      .refine((p) => PASSWORD_RULES.every((rule) => rule.test(p)), {
        message: "Password does not meet all requirements below.",
      })
      .refine((p) => !COMMON_WEAK_PASSWORDS.has(p.toLowerCase()), {
        message: "This password is too common. Please choose a stronger password.",
      }),
    confirm_password: z.string().min(1, "Please confirm your password."),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords do not match.",
    path: ["confirm_password"],
  })
  .refine((data) => data.password.toLowerCase() !== data.email.toLowerCase(), {
    message: "Password must not be the same as your email.",
    path: ["password"],
  });
export type RegisterFormValues = z.infer<typeof registerSchema>;
