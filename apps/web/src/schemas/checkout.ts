import { z } from "zod";

export const shippingAddressSchema = z.object({
  full_name: z.string().min(1, "Full name is required."),
  line1: z.string().min(1, "Street address is required."),
  line2: z.string().optional(),
  city: z.string().min(1, "City is required."),
  state: z.string().min(1, "State / province is required."),
  postal_code: z.string().min(1, "Postal code is required."),
  country: z.string().min(1, "Country is required."),
  phone: z.string().min(1, "Phone number is required."),
});
export type ShippingAddressFormValues = z.infer<typeof shippingAddressSchema>;
