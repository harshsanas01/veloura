import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { PasswordInput } from "@/components/ui/PasswordInput";
import { useLogin } from "@/hooks/useAuth";
import { type LoginFormValues, loginSchema } from "@/schemas/auth";

export function LoginPage() {
  const login = useLogin();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/account";

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({ resolver: zodResolver(loginSchema) });

  async function onSubmit(values: LoginFormValues) {
    await login.mutateAsync(values, { onSuccess: () => navigate(from, { replace: true }) });
  }

  return (
    <div className="container-veloura flex min-h-[70vh] items-center justify-center py-16">
      <div className="w-full max-w-sm">
        <h1 className="text-center font-display text-3xl text-ink">Welcome Back</h1>
        <p className="mt-2 text-center text-sm text-ink-secondary">Sign in to continue to Veloura.</p>

        <form onSubmit={handleSubmit(onSubmit)} className="mt-8 flex flex-col gap-4">
          <Input label="Email" type="email" autoComplete="email" {...register("email")} error={errors.email?.message} />
          <PasswordInput
            label="Password"
            autoComplete="current-password"
            {...register("password")}
            error={errors.password?.message}
          />
          <Button type="submit" size="lg" isLoading={login.isPending} className="mt-2">
            Sign In
          </Button>
        </form>

        <div className="mt-6 rounded border border-border bg-surface px-4 py-3 text-xs text-ink-secondary">
          Demo accounts — admin@veloura.com / AdminPass123! · customer@veloura.com / CustomerPass123!
        </div>

        <p className="mt-6 text-center text-sm text-ink-secondary">
          New to Veloura?{" "}
          <Link to="/register" className="font-medium text-burgundy hover:text-burgundy-hover">
            Create an account
          </Link>
        </p>
      </div>
    </div>
  );
}
