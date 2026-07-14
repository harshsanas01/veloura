import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="container-veloura flex min-h-[60vh] flex-col items-center justify-center text-center">
      <span className="font-display text-7xl text-burgundy">404</span>
      <h1 className="mt-4 font-display text-3xl text-ink">Page not found</h1>
      <p className="mt-2 max-w-sm text-sm text-ink-secondary">
        The page you're looking for doesn't exist or has moved.
      </p>
      <Link to="/" className="btn-primary mt-6">
        Back to Home
      </Link>
    </div>
  );
}
