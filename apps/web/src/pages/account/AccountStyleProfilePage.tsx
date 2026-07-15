import { useEffect, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { useStyleProfile, useUpdateStyleProfile } from "@/hooks/useAccount";

const GENDER_OPTIONS = [
  { value: "", label: "No preference" },
  { value: "women", label: "Women's" },
  { value: "men", label: "Men's" },
  { value: "unisex", label: "Unisex" },
];

const STYLE_OPTIONS = ["casual", "formal", "business-casual", "streetwear", "minimal"];
const OCCASION_OPTIONS = ["casual", "date-night", "business-casual", "vacation", "wedding", "party", "active", "formal"];

function TagPicker({
  label,
  options,
  selected,
  onToggle,
}: {
  label: string;
  options: string[];
  selected: string[];
  onToggle: (value: string) => void;
}) {
  return (
    <div>
      <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-ink">{label}</p>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => {
          const active = selected.includes(option);
          return (
            <button
              key={option}
              type="button"
              onClick={() => onToggle(option)}
              className={`rounded-full border px-3 py-1.5 text-xs font-medium capitalize transition-colors ${
                active ? "border-burgundy bg-burgundy text-surface" : "border-border text-ink hover:border-ink"
              }`}
            >
              {option.replace("-", " ")}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function CommaListInput({
  label,
  placeholder,
  values,
  onChange,
}: {
  label: string;
  placeholder: string;
  values: string[];
  onChange: (values: string[]) => void;
}) {
  const [text, setText] = useState(values.join(", "));
  useEffect(() => setText(values.join(", ")), [values]);
  return (
    <Input
      label={label}
      placeholder={placeholder}
      value={text}
      onChange={(e) => setText(e.target.value)}
      onBlur={() =>
        onChange(
          text
            .split(",")
            .map((v) => v.trim())
            .filter(Boolean),
        )
      }
    />
  );
}

export function AccountStyleProfilePage() {
  const { data: profile, isLoading } = useStyleProfile();
  const updateStyleProfile = useUpdateStyleProfile();

  const [genderPresentation, setGenderPresentation] = useState("");
  const [preferredColors, setPreferredColors] = useState<string[]>([]);
  const [dislikedColors, setDislikedColors] = useState<string[]>([]);
  const [preferredStyles, setPreferredStyles] = useState<string[]>([]);
  const [favoriteOccasions, setFavoriteOccasions] = useState<string[]>([]);
  const [preferredBrands, setPreferredBrands] = useState<string[]>([]);
  const [budgetMin, setBudgetMin] = useState<string>("");
  const [budgetMax, setBudgetMax] = useState<string>("");

  useEffect(() => {
    if (!profile) return;
    setGenderPresentation(profile.gender_presentation ?? "");
    setPreferredColors(profile.preferred_colors);
    setDislikedColors(profile.disliked_colors);
    setPreferredStyles(profile.preferred_styles);
    setFavoriteOccasions(profile.favorite_occasions);
    setPreferredBrands(profile.preferred_brands);
    setBudgetMin(profile.budget_min?.toString() ?? "");
    setBudgetMax(profile.budget_max?.toString() ?? "");
  }, [profile]);

  function toggle(list: string[], setList: (v: string[]) => void, value: string) {
    setList(list.includes(value) ? list.filter((v) => v !== value) : [...list, value]);
  }

  function handleSave() {
    updateStyleProfile.mutate({
      gender_presentation: genderPresentation || null,
      preferred_colors: preferredColors,
      disliked_colors: dislikedColors,
      preferred_styles: preferredStyles,
      favorite_occasions: favoriteOccasions,
      preferred_brands: preferredBrands,
      budget_min: budgetMin ? Number(budgetMin) : null,
      budget_max: budgetMax ? Number(budgetMax) : null,
    });
  }

  if (isLoading) {
    return <div className="skeleton h-96 w-full rounded-lg" />;
  }

  return (
    <div className="flex flex-col gap-6 rounded-lg border border-border bg-surface p-6">
      <div>
        <h2 className="font-display text-xl text-ink">Style Profile</h2>
        <p className="mt-1 text-sm text-ink-secondary">
          Tell the AI stylist what you like - it uses this whenever you're signed in.
        </p>
      </div>

      <Select
        label="Preferred Gender Presentation"
        value={genderPresentation}
        onChange={(e) => setGenderPresentation(e.target.value)}
      >
        {GENDER_OPTIONS.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </Select>

      <TagPicker
        label="Preferred Styles"
        options={STYLE_OPTIONS}
        selected={preferredStyles}
        onToggle={(v) => toggle(preferredStyles, setPreferredStyles, v)}
      />
      <TagPicker
        label="Favorite Occasions"
        options={OCCASION_OPTIONS}
        selected={favoriteOccasions}
        onToggle={(v) => toggle(favoriteOccasions, setFavoriteOccasions, v)}
      />

      <CommaListInput
        label="Favorite Colors (comma separated)"
        placeholder="black, burgundy, cream"
        values={preferredColors}
        onChange={setPreferredColors}
      />
      <CommaListInput
        label="Disliked Colors (comma separated)"
        placeholder="neon green, orange"
        values={dislikedColors}
        onChange={setDislikedColors}
      />
      <CommaListInput
        label="Favorite Brands (comma separated)"
        placeholder="Maison Aster, North & Ash"
        values={preferredBrands}
        onChange={setPreferredBrands}
      />

      <div className="grid grid-cols-2 gap-3">
        <Input
          label="Typical Budget Min ($)"
          type="number"
          min={0}
          value={budgetMin}
          onChange={(e) => setBudgetMin(e.target.value)}
        />
        <Input
          label="Typical Budget Max ($)"
          type="number"
          min={0}
          value={budgetMax}
          onChange={(e) => setBudgetMax(e.target.value)}
        />
      </div>

      <Button onClick={handleSave} isLoading={updateStyleProfile.isPending} className="self-start">
        Save Style Profile
      </Button>
    </div>
  );
}
