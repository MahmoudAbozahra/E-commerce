import type { components } from "@/shared/api/generated/schema";

export type Product = components["schemas"]["ProductList"];
export type ProductDetail = components["schemas"]["ProductDetail"];
export type ProductVariant = components["schemas"]["Variant"];
export type ProductImage = components["schemas"]["ProductImage"];
export type Category = components["schemas"]["Category"];
export type Brand = components["schemas"]["Brand"];
export type Cart = components["schemas"]["Cart"];
export type CartItem = components["schemas"]["CartItem"];
export type Address = components["schemas"]["Address"];
export type ShippingMethod = components["schemas"]["ShippingMethod"];
export type Order = components["schemas"]["Order"];
export type User = components["schemas"]["User"];
export type Review = components["schemas"]["Review"];

export type Paginated<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type NormalizedApiError = {
  code: string;
  message: string;
  fields: Record<string, string[]>;
};
