import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { PasswordInput } from "@/components/ui/PasswordInput";
import { PasswordStrengthChecklist } from "@/components/ui/PasswordStrengthChecklist";
import { useRegister } from "@/hooks/useAuth";
import { type RegisterFormValues, registerSchema } from "@/schemas/auth";

export function RegisterPage() {
  const registerUser = useRegister();
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<RegisterFormValues>({ resolver: zodResolver(registerSchema) });

  const password = watch("password") ?? "";

  async function onSubmit(values: RegisterFormValues) {
    await registerUser.mutateAsync(values, { onSuccess: () => navigate("/account") });
  }

  return (
    <div className="container-veloura flex min-h-[70vh] items-center justify-center py-16">
      <div className="w-full max-w-sm">
        <h1 className="text-center font-display text-3xl text-ink">Create Your Account</h1>
        <p className="mt-2 text-center text-sm text-ink-secondary">Join Veloura for a personalized styling experience.</p>

        <form onSubmit={handleSubmit(onSubmit)} className="mt-8 flex flex-col gap-4" noValidate>
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="First Name"
              autoComplete="given-name"
              {...register("first_name")}
              error={errors.first_name?.message}
            />
            <Input
              label="Last Name"
              autoComplete="family-name"
              {...register("last_name")}
              error={errors.last_name?.message}
            />
          </div>
          <Input label="Email" type="email" autoComplete="email" {...register("email")} error={errors.email?.message} />
          <div className="flex flex-col gap-2">
            <PasswordInput
              label="Password"
              autoComplete="new-password"
              {...register("password")}
              error={errors.password?.message}
            />
            <PasswordStrengthChecklist password={password} />
          </div>
          <PasswordInput
            label="Confirm Password"
            autoComplete="new-password"
            {...register("confirm_password")}
            error={errors.confirm_password?.message}
          />
          <Button type="submit" size="lg" isLoading={registerUser.isPending} className="mt-2">
            Create Account
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-ink-secondary">
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-burgundy hover:text-burgundy-hover">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
