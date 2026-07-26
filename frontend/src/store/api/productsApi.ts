import { baseApi } from "@/store/api/baseApi";
import { buildProductQueryString } from "@/lib/product-query";
import type {
  ApiEnvelope,
  Paginated,
  Product,
  ProductQueryParams,
  Review,
  ReviewSubmitRequest,
} from "@/types/api";

export const productsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getProducts: builder.query<Paginated<Product>, ProductQueryParams | void>({
      query: (params) => `/products${buildProductQueryString(params ?? {})}`,
      transformResponse: (res: ApiEnvelope<Paginated<Product>>) => res.data,
      providesTags: (result) =>
        result
          ? [
              ...result.items.map((p) => ({
                type: "Product" as const,
                id: p.id,
              })),
              { type: "Product" as const, id: "LIST" },
            ]
          : [{ type: "Product" as const, id: "LIST" }],
    }),

    getProductBySlug: builder.query<Product, string>({
      query: (slug) => `/products/${slug}`,
      transformResponse: (res: ApiEnvelope<Product>) => res.data,
      providesTags: (result) =>
        result ? [{ type: "Product", id: result.id }] : [],
    }),

    getFeaturedProducts: builder.query<Product[], void>({
      query: () => "/products/featured",
      transformResponse: (res: ApiEnvelope<Product[]>) => res.data,
      providesTags: [{ type: "Product", id: "FEATURED" }],
    }),

    getBestsellers: builder.query<Product[], void>({
      query: () => "/products/bestsellers",
      transformResponse: (res: ApiEnvelope<Product[]>) => res.data,
      providesTags: [{ type: "Product", id: "BESTSELLERS" }],
    }),

    getNewArrivals: builder.query<Product[], void>({
      query: () => "/products/new-arrivals",
      transformResponse: (res: ApiEnvelope<Product[]>) => res.data,
      providesTags: [{ type: "Product", id: "NEW_ARRIVALS" }],
    }),

    getReviews: builder.query<Review[], string>({
      query: (productId) => `/products/${productId}/reviews`,
      transformResponse: (res: ApiEnvelope<Review[]>) => res.data,
      providesTags: (_result, _error, productId) => [
        { type: "Reviews", id: productId },
      ],
    }),

    // Invalidates both the review list (so <ReviewList> refetches with the
    // new entry) and the product itself (so avgRating/reviewCount refresh
    // wherever that product is shown) — matches the spec's
    // `invalidatesTags: ['Reviews', productId]` intent, expressed as proper
    // RTK Query tag objects.
    submitReview: builder.mutation<Review, ReviewSubmitRequest>({
      query: ({ productId, ...body }) => ({
        url: `/products/${productId}/reviews`,
        method: "POST",
        body,
      }),
      transformResponse: (res: ApiEnvelope<Review>) => res.data,
      invalidatesTags: (_result, _error, arg) => [
        { type: "Reviews", id: arg.productId },
        { type: "Product", id: arg.productId },
      ],
    }),
  }),
  overrideExisting: false,
});

export const {
  useGetProductsQuery,
  useGetProductBySlugQuery,
  useGetFeaturedProductsQuery,
  useGetBestsellersQuery,
  useGetNewArrivalsQuery,
  useGetReviewsQuery,
  useSubmitReviewMutation,
} = productsApi;
