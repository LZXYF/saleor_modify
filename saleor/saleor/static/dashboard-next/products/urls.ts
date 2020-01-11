import { stringify as stringifyQs } from "qs";
import urlJoin from "url-join";

import { ActiveTab, BulkAction, Dialog, Filters, Pagination } from "../types";

const productSection = "/products/";

export const productAddPath = urlJoin(productSection, "add");
export const productAddUrl = productAddPath;

export const productListPath = productSection;
export type ProductListUrlDialog =
  | "publish"
  | "unpublish"
  | "delete"
  | "save-search"
  | "delete-search";
export enum ProductListUrlFiltersEnum {
  isPublished = "isPublished",
  priceFrom = "priceFrom",
  priceTo = "priceTo",
  status = "status",
  query = "query"
}
export type ProductListUrlFilters = Filters<ProductListUrlFiltersEnum>;
export type ProductListUrlQueryParams = BulkAction &
  Dialog<ProductListUrlDialog> &
  ProductListUrlFilters &
  Pagination &
  ActiveTab;
export const productListUrl = (params?: ProductListUrlQueryParams): string =>
  productListPath + "?" + stringifyQs(params);

export const productPath = (id: string) => urlJoin(productSection + id);
export type ProductUrlDialog = "remove";
export type ProductUrlQueryParams = BulkAction &
  Dialog<"remove" | "remove-variants">;
export const productUrl = (id: string, params?: ProductUrlQueryParams) =>
  productPath(encodeURIComponent(id)) + "?" + stringifyQs(params);

export const productVariantEditPath = (productId: string, variantId: string) =>
  urlJoin(productSection, productId, "variant", variantId);
export type ProductVariantEditUrlDialog = "remove";
export type ProductVariantEditUrlQueryParams = Dialog<"remove">;
export const productVariantEditUrl = (
  productId: string,
  variantId: string,
  params?: ProductVariantEditUrlQueryParams
) =>
  productVariantEditPath(
    encodeURIComponent(productId),
    encodeURIComponent(variantId)
  ) +
  "?" +
  stringifyQs(params);

export const productVariantAddPath = (productId: string) =>
  urlJoin(productSection, productId, "variant/add");
export const productVariantAddUrl = (productId: string) =>
  productVariantAddPath(encodeURIComponent(productId));

export const productImagePath = (productId: string, imageId: string) =>
  urlJoin(productSection, productId, "image", imageId);
export type ProductImageUrlDialog = "remove";
export type ProductImageUrlQueryParams = Dialog<"remove">;
export const productImageUrl = (
  productId: string,
  imageId: string,
  params?: ProductImageUrlQueryParams
) =>
  productImagePath(encodeURIComponent(productId), encodeURIComponent(imageId)) +
  "?" +
  stringifyQs(params);
