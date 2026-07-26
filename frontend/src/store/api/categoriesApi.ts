import { baseApi } from "@/store/api/baseApi";
import type { ApiEnvelope, Category, CategoryWithProducts } from "@/types/api";

export const categoriesApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getCategories: builder.query<Category[], void>({
      query: () => "/categories",
      transformResponse: (res: ApiEnvelope<Category[]>) => res.data,
      providesTags: [{ type: "Category", id: "LIST" }],
    }),

    getCategoryWithProducts: builder.query<
      CategoryWithProducts,
      { slug: string; page?: number }
    >({
      query: ({ slug, page }) =>
        `/categories/${slug}${page ? `?page=${page}` : ""}`,
      transformResponse: (res: ApiEnvelope<CategoryWithProducts>) => res.data,
      providesTags: (result) =>
        result
          ? [
              { type: "Category", id: result.slug },
              { type: "Category", id: "LIST" },
            ]
          : [{ type: "Category", id: "LIST" }],
    }),
  }),
  overrideExisting: false,
});

export const { useGetCategoriesQuery, useGetCategoryWithProductsQuery } =
  categoriesApi;
