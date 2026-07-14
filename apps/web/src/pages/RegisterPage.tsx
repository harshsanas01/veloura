import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useRegister } from "@/hooks/useAuth";
import { type RegisterFormValues, registerSchema } from "@/schemas/auth";

export function RegisterPage() {
  const registerUser = useRegister();
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterFormValues>({ resolver: zodResolver(registerSchema) });

  async function onSubmit(values: RegisterFormValues) {
    await registerUser.mutateAsync(values, { onSuccess: () => navigate("/account") });
  }

  return (
    <div className="container-veloura flex min-h-[70vh] items-center justify-center py-16">
      <div className="w-full max-w-sm">
        <h1 className="text-center font-display text-3xl text-ink">Create Your Account</h1>
        <p className="mt-2 text-center text-sm text-ink-secondary">Join Veloura for a personalized styling experience.</p>

        <form onSubmit={handleSubmit(onSubmit)} className="mt-8 flex flex-col gap-4">
          <Input label="Full Name" autoComplete="name" {...register("full_name")} error={errors.full_name?.message} />
          <Input label="Email" type="email" autoComplete="email" {...register("email")} error={errors.email?.message} />
          <Input
            label="Password"
            type="password"
            autoComplete="new-password"
            {...register("password")}
            error={errors.password?.message}
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
