import { Modal } from "@/components/ui/Modal";

const CLOTHING_ROWS = [
  { size: "XS", chest: "32-34", waist: "24-26", hips: "34-36" },
  { size: "S", chest: "35-37", waist: "27-29", hips: "37-39" },
  { size: "M", chest: "38-40", waist: "30-32", hips: "40-42" },
  { size: "L", chest: "41-43", waist: "33-36", hips: "43-46" },
  { size: "XL", chest: "44-46", waist: "37-40", hips: "47-50" },
  { size: "XXL", chest: "47-49", waist: "41-44", hips: "51-54" },
];

const SHOE_ROWS = [
  { us: "7", uk: "6", eu: "40", cm: "25" },
  { us: "8", uk: "7", eu: "41", cm: "26" },
  { us: "9", uk: "8", eu: "42", cm: "27" },
  { us: "10", uk: "9", eu: "43", cm: "28" },
  { us: "11", uk: "10", eu: "44", cm: "29" },
  { us: "12", uk: "11", eu: "45", cm: "30" },
];

export function SizeGuideModal({
  isOpen,
  onClose,
  isShoe,
}: {
  isOpen: boolean;
  onClose: () => void;
  isShoe: boolean;
}) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Size Guide">
      <p className="mb-4 text-sm text-ink-secondary">
        Measurements are in inches (clothing) or as marked (shoes). If you're between sizes, we recommend sizing up.
      </p>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-border text-xs uppercase tracking-wider text-ink-secondary">
              {isShoe ? (
                <>
                  <th className="py-2">US</th>
                  <th className="py-2">UK</th>
                  <th className="py-2">EU</th>
                  <th className="py-2">CM</th>
                </>
              ) : (
                <>
                  <th className="py-2">Size</th>
                  <th className="py-2">Chest</th>
                  <th className="py-2">Waist</th>
                  <th className="py-2">Hips</th>
                </>
              )}
            </tr>
          </thead>
          <tbody>
            {isShoe
              ? SHOE_ROWS.map((row) => (
                  <tr key={row.us} className="border-b border-border/60">
                    <td className="py-2 font-medium text-ink">{row.us}</td>
                    <td className="py-2 text-ink-secondary">{row.uk}</td>
                    <td className="py-2 text-ink-secondary">{row.eu}</td>
                    <td className="py-2 text-ink-secondary">{row.cm}</td>
                  </tr>
                ))
              : CLOTHING_ROWS.map((row) => (
                  <tr key={row.size} className="border-b border-border/60">
                    <td className="py-2 font-medium text-ink">{row.size}</td>
                    <td className="py-2 text-ink-secondary">{row.chest}</td>
                    <td className="py-2 text-ink-secondary">{row.waist}</td>
                    <td className="py-2 text-ink-secondary">{row.hips}</td>
                  </tr>
                ))}
          </tbody>
        </table>
      </div>
    </Modal>
  );
}
