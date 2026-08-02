import { baseApi } from "@/store/api/baseApi";
import type {
  AdminCategory,
  AdminCategoryInput,
  ApiEnvelope,
} from "@/types/api";

export const adminCategoriesApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getAdminCategories: builder.query<AdminCategory[], void>({
      query: () => "/admin/categories",
      transformResponse: (res: ApiEnvelope<AdminCategory[]>) => res.data,
      providesTags: (result) =>
        result
          ? [
              ...result.map((c) => ({ type: "Category" as const, id: c.id })),
              { type: "Category" as const, id: "ADMIN_LIST" },
            ]
          : [{ type: "Category" as const, id: "ADMIN_LIST" }],
    }),

    createAdminCategory: builder.mutation<AdminCategory, AdminCategoryInput>({
      query: (body) => ({ url: "/admin/categories", method: "POST", body }),
      transformResponse: (res: ApiEnvelope<AdminCategory>) => res.data,
      invalidatesTags: [{ type: "Category", id: "ADMIN_LIST" }],
    }),

    updateAdminCategory: builder.mutation<
      AdminCategory,
      { id: string } & AdminCategoryInput
    >({
      query: ({ id, ...body }) => ({
        url: `/admin/categories/${id}`,
        method: "PUT",
        body,
      }),
      transformResponse: (res: ApiEnvelope<AdminCategory>) => res.data,
      invalidatesTags: (_result, _error, arg) => [
        { type: "Category", id: arg.id },
        { type: "Category", id: "ADMIN_LIST" },
      ],
    }),

    deleteAdminCategory: builder.mutation<void, string>({
      query: (id) => ({ url: `/admin/categories/${id}`, method: "DELETE" }),
      invalidatesTags: [{ type: "Category", id: "ADMIN_LIST" }],
    }),

    reorderCategories: builder.mutation<AdminCategory[], string[]>({
      query: (orderedIds) => ({
        url: "/admin/categories/reorder",
        method: "PUT",
        body: { orderedIds },
      }),
      transformResponse: (res: ApiEnvelope<AdminCategory[]>) => res.data,
      invalidatesTags: [{ type: "Category", id: "ADMIN_LIST" }],
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetAdminCategoriesQuery,
  useCreateAdminCategoryMutation,
  useUpdateAdminCategoryMutation,
  useDeleteAdminCategoryMutation,
  useReorderCategoriesMutation,
} = adminCategoriesApi;
