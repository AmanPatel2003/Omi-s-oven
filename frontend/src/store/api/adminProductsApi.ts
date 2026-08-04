import { baseApi } from "@/store/api/baseApi";
import type {
  AdminProduct,
  AdminProductInput,
  AdminProductListParams,
  ApiEnvelope,
  Paginated,
  ProductImage,
  StockAdjustment,
} from "@/types/api";

function buildListQuery(params: AdminProductListParams = {}): string {
  const search = new URLSearchParams();
  if (params.page) search.set("page", String(params.page));
  if (params.pageSize) search.set("pageSize", String(params.pageSize));
  if (params.search) search.set("search", params.search);
  if (params.category) search.set("category", params.category);
  if (params.sort) search.set("sort", params.sort);
  if (params.sortDir) search.set("sortDir", params.sortDir);
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

function toApiProduct(body: AdminProductInput) {
  return {
    name: body.name,
    slug: body.slug,
    description: body.description,
    category: body.categoryId,
    price: body.price,
    discount_price: body.discountPrice,
    tags: body.tags,
    variants: body.variants,
    is_eggless: body.isEggless,
    stock: body.stock,
    low_stock_threshold: body.lowStockThreshold,
  };
}

export const adminProductsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getAdminProducts: builder.query<
      Paginated<AdminProduct>,
      AdminProductListParams | void
    >({
      query: (params) => `/admin/products${buildListQuery(params ?? {})}`,
      transformResponse: (res: ApiEnvelope<Paginated<AdminProduct>>) =>
        res.data,
      providesTags: (result) =>
        result
          ? [
              ...result.items.map((p) => ({
                type: "Product" as const,
                id: p.id,
              })),
              { type: "Product" as const, id: "ADMIN_LIST" },
            ]
          : [{ type: "Product" as const, id: "ADMIN_LIST" }],
    }),

    getAdminProductById: builder.query<AdminProduct, string>({
      query: (id) => `/admin/products/${id}`,
      transformResponse: (res: ApiEnvelope<AdminProduct>) => res.data,
      providesTags: (_result, _error, id) => [{ type: "Product", id }],
    }),

    createAdminProduct: builder.mutation<AdminProduct, AdminProductInput>({
      query: (body) => ({
        url: "/admin/products",
        method: "POST",
        body: toApiProduct(body),
      }),
      transformResponse: (res: ApiEnvelope<AdminProduct>) => res.data,
      invalidatesTags: [{ type: "Product", id: "ADMIN_LIST" }],
    }),

    updateAdminProduct: builder.mutation<
      AdminProduct,
      { id: string } & AdminProductInput
    >({
      query: ({ id, ...body }) => ({
        url: `/admin/products/${id}`,
        method: "PUT",
        body: toApiProduct(body),
      }),
      transformResponse: (res: ApiEnvelope<AdminProduct>) => res.data,
      invalidatesTags: (_result, _error, arg) => [
        { type: "Product", id: arg.id },
        { type: "Product", id: "ADMIN_LIST" },
        { type: "Product", id: "LOW_STOCK" },
      ],
    }),

    toggleProductAvailability: builder.mutation<
      AdminProduct,
      { id: string; isAvailable: boolean }
    >({
      query: ({ id, isAvailable }) => ({
        url: `/admin/products/${id}/toggle`,
        method: "PUT",
        body: { is_available: isAvailable },
      }),
      transformResponse: (res: ApiEnvelope<AdminProduct>) => res.data,
      invalidatesTags: (_result, _error, arg) => [
        { type: "Product", id: arg.id },
        { type: "Product", id: "ADMIN_LIST" },
      ],
    }),

    toggleProductFeatured: builder.mutation<
      AdminProduct,
      { id: string; isFeatured: boolean }
    >({
      query: ({ id, isFeatured }) => ({
        url: `/admin/products/${id}/featured`,
        method: "PUT",
        body: { is_featured: isFeatured },
      }),
      transformResponse: (res: ApiEnvelope<AdminProduct>) => res.data,
      invalidatesTags: (_result, _error, arg) => [
        { type: "Product", id: arg.id },
        { type: "Product", id: "ADMIN_LIST" },
      ],
    }),

    uploadProductImages: builder.mutation<
      ProductImage[],
      { id: string; files: File[] }
    >({
      query: ({ id, files }) => {
        const formData = new FormData();
        files.forEach((file) => formData.append("files", file));
        return {
          url: `/admin/products/${id}/images`,
          method: "POST",
          body: formData,
        };
      },
      transformResponse: (res: ApiEnvelope<ProductImage[]>) => res.data,
      invalidatesTags: (_result, _error, arg) => [
        { type: "Product", id: arg.id },
      ],
    }),

    deleteProductImage: builder.mutation<
      void,
      { productId: string; imageId: string }
    >({
      query: ({ productId, imageId }) => ({
        url: `/admin/products/${productId}/images/${imageId}`,
        method: "DELETE",
      }),
      invalidatesTags: (_result, _error, arg) => [
        { type: "Product", id: arg.productId },
      ],
    }),

    updateProductStock: builder.mutation<
      AdminProduct,
      { id: string } & StockAdjustment
    >({
      query: ({ id, ...body }) => ({
        url: `/admin/products/${id}/stock`,
        method: "PUT",
        body,
      }),
      transformResponse: (res: ApiEnvelope<AdminProduct>) => res.data,
      invalidatesTags: (_result, _error, arg) => [
        { type: "Product", id: arg.id },
        { type: "Product", id: "ADMIN_LIST" },
        { type: "Product", id: "LOW_STOCK" },
      ],
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetAdminProductsQuery,
  useGetAdminProductByIdQuery,
  useCreateAdminProductMutation,
  useUpdateAdminProductMutation,
  useToggleProductAvailabilityMutation,
  useToggleProductFeaturedMutation,
  useUploadProductImagesMutation,
  useDeleteProductImageMutation,
  useUpdateProductStockMutation,
} = adminProductsApi;
