import { motion } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";

import { ProductRail } from "@/components/product/ProductRail";
import { useProducts } from "@/hooks/useProducts";
import { useToastStore } from "@/store/toastStore";

const EXAMPLE_PROMPTS = [
  "Pool party outfit under $150",
  "All-black date night look",
  "Casual summer, blue and white",
  "Business-casual for the office",
];

const EDITORIALS = [
  {
    title: "Coastal Getaway",
    copy: "Breezy linens and warm neutrals for your next escape.",
    image: "https://images.unsplash.com/photo-1618932260643-eee4a2f652a6?w=900&q=80",
    to: "/shop?category=swimwear",
  },
  {
    title: "City Tailoring",
    copy: "Sharp silhouettes for the modern workweek.",
    image: "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=900&q=80",
    to: "/shop?category=trousers",
  },
  {
    title: "Evening Edit",
    copy: "Considered pieces for after-dark occasions.",
    image: "https://images.unsplash.com/photo-1571908599407-cdb918ed83bf?w=900&q=80",
    to: "/shop?category=dresses",
  },
];

const TESTIMONIALS = [
  {
    quote:
      "The AI stylist put together a date-night look in seconds — and every piece was actually in stock. Genuinely useful.",
    name: "Priya M.",
    initials: "PM",
  },
  {
    quote: "Fast, elegant, and the quality is exactly what the photos promised. Veloura is my go-to now.",
    name: "Daniel K.",
    initials: "DK",
  },
  {
    quote: "I love that I can describe a vibe and get real outfit suggestions, not just generic search results.",
    name: "Sofia R.",
    initials: "SR",
  },
];

function fadeUp(delay = 0) {
  return {
    initial: { opacity: 0, y: 24 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: 0.5, delay },
  };
}

export function HomePage() {
  const { data: featured, isLoading: featuredLoading } = useProducts({ sort: "featured", page_size: 8 });
  const { data: newArrivals, isLoading: newArrivalsLoading } = useProducts({ sort: "newest", page_size: 8 });
  const { data: womensEdit, isLoading: womensLoading } = useProducts({ gender: "women", sort: "featured", page_size: 8 });
  const { data: mensEdit, isLoading: mensLoading } = useProducts({ gender: "men", sort: "featured", page_size: 8 });

  const [email, setEmail] = useState("");
  const push = useToastStore((s) => s.push);

  function handleNewsletterSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim()) return;
    push("You're on the list. Welcome to Veloura.", "success");
    setEmail("");
  }

  return (
    <div>
      {/* Hero */}
      <section className="relative flex min-h-[86vh] items-end overflow-hidden bg-ink">
        <img
          src="https://images.unsplash.com/photo-1483985988355-763728e1935b?w=1600&q=80"
          alt="Veloura editorial"
          className="absolute inset-0 h-full w-full object-cover opacity-70"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-ink via-ink/20 to-transparent" />
        <div className="container-veloura relative z-10 pb-20 pt-32">
          <motion.h1
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7 }}
            className="max-w-2xl font-display text-5xl leading-[1.05] text-surface sm:text-6xl lg:text-7xl"
          >
            Style, Curated Around You.
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.15 }}
            className="mt-5 max-w-lg text-base text-surface/85 sm:text-lg"
          >
            Discover modern fashion for every occasion, with intelligent styling recommendations
            tailored to your taste.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.3 }}
            className="mt-8 flex flex-wrap gap-4"
          >
            <Link to="/shop/women" className="btn-primary">
              Shop Women
            </Link>
            <Link
              to="/shop/men"
              className="btn rounded border border-surface bg-transparent px-6 py-3 text-surface hover:bg-surface hover:text-ink"
            >
              Shop Men
            </Link>
          </motion.div>
        </div>
      </section>

      {/* AI Stylist promo */}
      <section className="bg-rose/25">
        <div className="container-veloura grid items-center gap-10 py-16 lg:grid-cols-2">
          <motion.div {...fadeUp()}>
            <span className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-burgundy">
              <Sparkles className="h-4 w-4" /> AI Stylist
            </span>
            <h2 className="mt-3 font-display text-4xl text-ink">Meet Your AI Stylist</h2>
            <p className="mt-3 max-w-md text-ink-secondary">
              Describe the occasion, mood, colors, and budget. Veloura will create complete looks
              using pieces available in our collection.
            </p>
            <Link to="/ai-stylist" className="btn-primary mt-6 inline-flex">
              Start Styling <ArrowRight className="h-4 w-4" />
            </Link>
          </motion.div>
          <motion.div {...fadeUp(0.15)} className="flex flex-wrap gap-3">
            {EXAMPLE_PROMPTS.map((prompt) => (
              <Link
                key={prompt}
                to="/ai-stylist"
                className="rounded-full border border-burgundy/30 bg-surface px-4 py-2.5 text-sm text-ink shadow-card transition-colors hover:border-burgundy hover:text-burgundy"
              >
                {prompt}
              </Link>
            ))}
          </motion.div>
        </div>
      </section>

      {/* New Arrivals */}
      <section className="container-veloura py-16">
        <motion.div {...fadeUp()} className="mb-8 flex items-end justify-between">
          <h2 className="font-display text-3xl text-ink">New Arrivals</h2>
          <Link to="/shop?sort=newest" className="text-sm font-medium text-burgundy hover:text-burgundy-hover">
            View All
          </Link>
        </motion.div>
        <ProductRail products={newArrivals?.items} isLoading={newArrivalsLoading} />
      </section>

      {/* Women's Edit */}
      <section className="bg-surface py-16">
        <div className="container-veloura">
          <motion.div {...fadeUp()} className="mb-8 flex items-end justify-between">
            <h2 className="font-display text-3xl text-ink">Women's Edit</h2>
            <Link to="/shop/women" className="text-sm font-medium text-burgundy hover:text-burgundy-hover">
              Shop Women
            </Link>
          </motion.div>
          <ProductRail products={womensEdit?.items} isLoading={womensLoading} />
        </div>
      </section>

      {/* Men's Edit */}
      <section className="container-veloura py-16">
        <motion.div {...fadeUp()} className="mb-8 flex items-end justify-between">
          <h2 className="font-display text-3xl text-ink">Men's Edit</h2>
          <Link to="/shop/men" className="text-sm font-medium text-burgundy hover:text-burgundy-hover">
            Shop Men
          </Link>
        </motion.div>
        <ProductRail products={mensEdit?.items} isLoading={mensLoading} />
      </section>

      {/* Editorial collection cards */}
      <section className="bg-surface py-16">
        <div className="container-veloura">
          <motion.h2 {...fadeUp()} className="mb-8 font-display text-3xl text-ink">
            Shop the Edit
          </motion.h2>
          <div className="grid gap-5 sm:grid-cols-3">
            {EDITORIALS.map((editorial, i) => (
              <motion.div key={editorial.title} {...fadeUp(i * 0.1)}>
                <Link to={editorial.to} className="group block overflow-hidden rounded-lg">
                  <div className="relative aspect-[4/5] overflow-hidden">
                    <img
                      src={editorial.image}
                      alt={editorial.title}
                      className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-105"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-ink/70 via-transparent to-transparent" />
                    <div className="absolute bottom-0 left-0 p-5">
                      <h3 className="font-display text-2xl text-surface">{editorial.title}</h3>
                      <p className="mt-1 text-sm text-surface/85">{editorial.copy}</p>
                    </div>
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Styled by Veloura */}
      <section className="container-veloura py-16">
        <motion.div {...fadeUp()} className="mb-8 flex items-end justify-between">
          <h2 className="font-display text-3xl text-ink">Styled by Veloura</h2>
          <Link to="/ai-stylist" className="text-sm font-medium text-burgundy hover:text-burgundy-hover">
            Try the AI Stylist
          </Link>
        </motion.div>
        <ProductRail products={featured?.items} isLoading={featuredLoading} />
      </section>

      {/* Testimonials */}
      <section className="bg-ink py-16">
        <div className="container-veloura">
          <motion.h2 {...fadeUp()} className="mb-10 font-display text-3xl text-surface">
            Loved by the Veloura Community
          </motion.h2>
          <div className="grid gap-6 sm:grid-cols-3">
            {TESTIMONIALS.map((t, i) => (
              <motion.div
                key={t.name}
                {...fadeUp(i * 0.1)}
                className="rounded-lg border border-surface/10 bg-surface/5 p-6"
              >
                <p className="text-sm leading-relaxed text-surface/85">&ldquo;{t.quote}&rdquo;</p>
                <div className="mt-5 flex items-center gap-3">
                  <span className="flex h-9 w-9 items-center justify-center rounded-full bg-burgundy text-xs font-semibold text-surface">
                    {t.initials}
                  </span>
                  <span className="text-sm font-medium text-surface">{t.name}</span>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Newsletter */}
      <section className="bg-rose/25 py-16">
        <div className="container-veloura flex flex-col items-center text-center">
          <motion.h2 {...fadeUp()} className="font-display text-3xl text-ink">
            Join the List
          </motion.h2>
          <motion.p {...fadeUp(0.1)} className="mt-2 max-w-md text-sm text-ink-secondary">
            Early access to new arrivals, exclusive edits, and styling ideas from Veloura AI.
          </motion.p>
          <motion.form
            {...fadeUp(0.2)}
            onSubmit={handleNewsletterSubmit}
            className="mt-6 flex w-full max-w-sm gap-2"
          >
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Your email address"
              className="input-veloura"
            />
            <button type="submit" className="btn-primary shrink-0">
              Subscribe
            </button>
          </motion.form>
        </div>
      </section>
    </div>
  );
}
