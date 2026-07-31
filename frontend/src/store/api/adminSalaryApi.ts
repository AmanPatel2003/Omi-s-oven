import { baseApi } from "@/store/api/baseApi";
import type {
  ApiEnvelope,
  ProcessSalaryResponse,
  SalaryPreviewRow,
} from "@/types/api";

export const adminSalaryApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getSalaryPreview: builder.query<SalaryPreviewRow[], string>({
      query: (month) => `/admin/salary/calculate/${month}`,
      transformResponse: (res: ApiEnvelope<SalaryPreviewRow[]>) => res.data,
    }),

    processSalary: builder.mutation<ProcessSalaryResponse, string>({
      query: (month) => ({
        url: `/admin/salary/process/${month}`,
        method: "POST",
      }),
      transformResponse: (res: ApiEnvelope<ProcessSalaryResponse>) => res.data,
    }),
  }),
  overrideExisting: false,
});

export const { useGetSalaryPreviewQuery, useProcessSalaryMutation } =
  adminSalaryApi;
