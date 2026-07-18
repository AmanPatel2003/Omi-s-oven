import Link from "next/link";

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col items-center justify-center gap-4 px-4 text-center">
      <h1 className="font-display text-3xl font-semibold text-crust-900">
        The Bakery
      </h1>
      <p className="text-crust-600">
        Products, cart, and checkout modules land in later steps of the build
        prompt — this is just Module 1 (Auth) wired end to end.
      </p>
      <Link
        href="/auth/login"
        className="rounded-xl bg-crust-600 px-4 py-2.5 text-sm font-medium text-crust-50"
      >
        Sign in
      </Link>
    </main>
  );
}
