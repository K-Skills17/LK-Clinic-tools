"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Header } from "@/components/layout/Header";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { EmptyState } from "@/components/shared/EmptyState";
import { useClinic } from "@/hooks/useClinic";
import { Star, Copy, Check, Sparkles } from "lucide-react";
import toast from "react-hot-toast";

interface GoogleReview {
  id: string;
  reviewer_name: string;
  rating: number;
  text: string;
  response_status: string;
  ai_response_options: { tone: string; text: string }[] | null;
  selected_response: string | null;
  review_date: string;
}

export default function ReviewResponsesPage() {
  const { fetchClinicData, postClinicData } = useClinic();
  const [reviews, setReviews] = useState<GoogleReview[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClinicData<{ reviews: GoogleReview[] }>("/google-reviews/pending-response")
      .then((data) => setReviews(data.reviews))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  async function generateResponses(reviewId: string) {
    try {
      const result = await postClinicData<{
        response_options: { tone: string; text: string }[];
      }>("/review-responses/generate", { review_id: reviewId });

      setReviews((prev) =>
        prev.map((r) =>
          r.id === reviewId
            ? { ...r, ai_response_options: result.response_options, response_status: "drafted" }
            : r
        )
      );
      toast.success("Respostas geradas!");
    } catch {
      toast.error("Erro ao gerar respostas.");
    }
  }

  function copyToClipboard(text: string) {
    navigator.clipboard.writeText(text);
    toast.success("Copiado!");
  }

  return (
    <DashboardLayout>
      <Header
        title="Respostas de Avaliacoes"
        subtitle="Gere respostas com IA para avaliacoes do Google"
      />

      {loading ? (
        <LoadingSpinner />
      ) : reviews.length === 0 ? (
        <EmptyState
          title="Nenhuma avaliacao pendente"
          description="Todas as avaliacoes ja foram respondidas."
        />
      ) : (
        <div className="space-y-6">
          {reviews.map((review) => (
            <div key={review.id} className="card">
              {/* Review header */}
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h4 className="font-semibold">{review.reviewer_name}</h4>
                  <div className="flex items-center gap-1 mt-1">
                    {Array.from({ length: 5 }, (_, i) => (
                      <Star
                        key={i}
                        size={14}
                        className={
                          i < review.rating
                            ? "text-yellow-400 fill-yellow-400"
                            : "text-gray-300"
                        }
                      />
                    ))}
                  </div>
                </div>
              </div>

              {/* Review text */}
              {review.text && (
                <p className="text-sm text-gray-700 mb-4 bg-gray-50 rounded-lg p-3">
                  &ldquo;{review.text}&rdquo;
                </p>
              )}

              {/* AI Response options */}
              {review.ai_response_options ? (
                <div className="space-y-3">
                  <p className="text-sm font-medium text-gray-700">
                    Opcoes de resposta:
                  </p>
                  {review.ai_response_options.map((option, i) => (
                    <div
                      key={i}
                      className="flex items-start gap-3 p-3 border border-gray-200 rounded-lg"
                    >
                      <div className="flex-1">
                        <span className="badge-info text-xs mb-1">
                          {option.tone}
                        </span>
                        <p className="text-sm text-gray-700 mt-1">
                          {option.text}
                        </p>
                      </div>
                      <button
                        onClick={() => copyToClipboard(option.text)}
                        className="btn-secondary flex items-center gap-1 text-xs"
                      >
                        <Copy size={12} />
                        Copiar
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <button
                  onClick={() => generateResponses(review.id)}
                  className="btn-primary flex items-center gap-2"
                >
                  <Sparkles size={16} />
                  Gerar Respostas com IA
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </DashboardLayout>
  );
}
