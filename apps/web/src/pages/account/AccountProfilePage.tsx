import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { PasswordInput } from "@/components/ui/PasswordInput";
import { PasswordStrengthChecklist } from "@/components/ui/PasswordStrengthChecklist";
import { useCurrentUser } from "@/hooks/useAuth";
import { useChangePassword, useDeleteAccount, useUpdateProfile } from "@/hooks/useAccount";
import { PASSWORD_RULES } from "@/schemas/auth";

const profileSchema = z.object({
  first_name: z.string().min(1, "First name is required.").max(120),
  last_name: z.string().max(120).optional().default(""),
  email: z.string().min(1, "Email is required").email("Enter a valid email address."),
});
type ProfileFormValues = z.infer<typeof profileSchema>;

const passwordSchema = z
  .object({
    current_password: z.string().min(1, "Current password is required."),
    new_password: z
      .string()
      .min(8, "Password must be at least 8 characters.")
      .refine((p) => PASSWORD_RULES.every((rule) => rule.test(p)), {
        message: "Password does not meet all requirements below.",
      }),
    confirm_new_password: z.string().min(1, "Please confirm your new password."),
  })
  .refine((data) => data.new_password === data.confirm_new_password, {
    message: "Passwords do not match.",
    path: ["confirm_new_password"],
  });
type PasswordFormValues = z.infer<typeof passwordSchema>;

export function AccountProfilePage() {
  const user = useCurrentUser();
  const updateProfile = useUpdateProfile();
  const changePassword = useChangePassword();
  const deleteAccount = useDeleteAccount();

  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deletePassword, setDeletePassword] = useState("");

  const profileForm = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    values: user
      ? { first_name: user.first_name, last_name: user.last_name, email: user.email }
      : undefined,
  });

  const passwordForm = useForm<PasswordFormValues>({ resolver: zodResolver(passwordSchema) });
  const newPassword = passwordForm.watch("new_password") ?? "";

  async function onProfileSubmit(values: ProfileFormValues) {
    await updateProfile.mutateAsync(values);
  }

  async function onPasswordSubmit(values: PasswordFormValues) {
    await changePassword.mutateAsync(values, { onSuccess: () => passwordForm.reset() });
  }

  return (
    <div className="flex flex-col gap-8">
      <section className="rounded-lg border border-border bg-surface p-6">
        <h2 className="font-display text-xl text-ink">Profile</h2>
        <form
          onSubmit={profileForm.handleSubmit(onProfileSubmit)}
          className="mt-4 flex flex-col gap-4 sm:max-w-sm"
        >
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="First Name"
              {...profileForm.register("first_name")}
              error={profileForm.formState.errors.first_name?.message}
            />
            <Input
              label="Last Name"
              {...profileForm.register("last_name")}
              error={profileForm.formState.errors.last_name?.message}
            />
          </div>
          <Input
            label="Email"
            type="email"
            {...profileForm.register("email")}
            error={profileForm.formState.errors.email?.message}
          />
          <Button type="submit" isLoading={updateProfile.isPending} className="self-start">
            Save Changes
          </Button>
        </form>
      </section>

      <section className="rounded-lg border border-border bg-surface p-6">
        <h2 className="font-display text-xl text-ink">Change Password</h2>
        <form
          onSubmit={passwordForm.handleSubmit(onPasswordSubmit)}
          className="mt-4 flex flex-col gap-4 sm:max-w-sm"
        >
          <PasswordInput
            label="Current Password"
            autoComplete="current-password"
            {...passwordForm.register("current_password")}
            error={passwordForm.formState.errors.current_password?.message}
          />
          <div className="flex flex-col gap-2">
            <PasswordInput
              label="New Password"
              autoComplete="new-password"
              {...passwordForm.register("new_password")}
              error={passwordForm.formState.errors.new_password?.message}
            />
            <PasswordStrengthChecklist password={newPassword} />
          </div>
          <PasswordInput
            label="Confirm New Password"
            autoComplete="new-password"
            {...passwordForm.register("confirm_new_password")}
            error={passwordForm.formState.errors.confirm_new_password?.message}
          />
          <Button type="submit" isLoading={changePassword.isPending} className="self-start">
            Update Password
          </Button>
        </form>
      </section>

      <section className="rounded-lg border border-error/30 bg-error/5 p-6">
        <h2 className="font-display text-xl text-ink">Delete Account</h2>
        <p className="mt-1 text-sm text-ink-secondary">
          This permanently deletes your account, orders, cart, and wishlist. This cannot be undone.
        </p>
        <Button variant="danger" className="mt-4" onClick={() => setDeleteOpen(true)}>
          Delete My Account
        </Button>
      </section>

      <Modal isOpen={deleteOpen} onClose={() => setDeleteOpen(false)} title="Delete your account?">
        <p className="text-sm text-ink-secondary">
          Enter your password to permanently delete your account. This action cannot be undone.
        </p>
        <div className="mt-4 flex flex-col gap-4">
          <PasswordInput
            label="Password"
            value={deletePassword}
            onChange={(e) => setDeletePassword(e.target.value)}
          />
          <div className="flex justify-end gap-3">
            <Button variant="ghost" onClick={() => setDeleteOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="danger"
              isLoading={deleteAccount.isPending}
              disabled={!deletePassword}
              onClick={() =>
                deleteAccount.mutate({ password: deletePassword, confirm: true })
              }
            >
              Permanently Delete
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
