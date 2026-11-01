"use client";

import { FormEvent, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { useToast } from "@/components/ui/Toast";
import { Badge, statusTone } from "@/components/ui/Badge";
import type { Review } from "@/types";

export default function ReviewDetailPage() {
  const params = useParams<{ id: string }>();
  const { push } = useToast();
  const [review, setReview] = useState<Review | null>(null);
  const [goalScore, setGoalScore] = useState("4");
  const [feedbackScore, setFeedbackScore] = useState("4");
  const [summary, setSummary] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .review(params.id)
      .then((r) => {
        setReview(r);
        setSummary(r.summary || "");
        if (r.goal_score != null) setGoalScore(String(r.goal_score));
        if (r.feedback_score != null) setFeedbackScore(String(r.feedback_score));
      })
      .catch((e) => setError(e instanceof ApiError ? e.detail : "Not found"));
  }, [params.id]);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!review) return;
    try {
      const updated = await api.submitReview(review.review_id, {
        summary,
        goal_score: Number(goalScore),
        feedback_score: Number(feedbackScore),
      });
      setReview(updated);
      push("Review submitted. Overall score is 50% goal + 50% feedback.", "success");
    } catch (err) {
      push(err instanceof ApiError ? err.detail : "Submit failed", "error");
    }
  }

  if (error) return <p className="text-rose-600">{error}</p>;
  if (!review) return <p className="text-sm text-slate-500">Loading…</p>;

  const overall =
    Number(goalScore) * 0.5 + Number(feedbackScore) * 0.5;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">{review.review_id}</h1>
        <p className="text-sm text-slate-500">
          {review.employee_name} reviewed by {review.reviewer_name} · {review.cycle_name} · v{review.version}
        </p>
        <Badge tone={statusTone(review.status)}>{review.status}</Badge>
      </div>
      <div className="card p-4 text-sm">
        <p>Required inputs: subject, reviewer, cycle, goal score, feedback score, and summary.</p>
        <p>Stored overall score: {review.overall_score ?? "not submitted"}</p>
      </div>
      <form onSubmit={submit} className="card space-y-3 p-4">
        <label className="text-sm">
          Goal score (1-5)
          <input className="input mt-1" type="number" step="0.1" min={1} max={5} value={goalScore} onChange={(e) => setGoalScore(e.target.value)} />
        </label>
        <label className="text-sm">
          Feedback score (1-5)
          <input className="input mt-1" type="number" step="0.1" min={1} max={5} value={feedbackScore} onChange={(e) => setFeedbackScore(e.target.value)} />
        </label>
        <p className="text-sm text-slate-500">Preview overall (0.5×goal + 0.5×feedback): {overall.toFixed(2)}</p>
        <textarea className="input" value={summary} onChange={(e) => setSummary(e.target.value)} placeholder="Review summary grounded in goals and feedback" />
        <button className="btn btn-primary" disabled={review.status === "submitted"}>
          Submit review
        </button>
      </form>
    </div>
  );
}
