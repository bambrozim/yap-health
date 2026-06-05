import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ScoreCard } from "./ScoreCard";

describe("ScoreCard", () => {
  it("shows label and score", () => {
    render(<ScoreCard label="Cardíaco" score={60} />);
    expect(screen.getByText("Cardíaco")).toBeTruthy();
    expect(screen.getByText("60")).toBeTruthy();
  });

  it("shows dash when score is null", () => {
    render(<ScoreCard label="Atividade" score={null} />);
    expect(screen.getByText("—")).toBeTruthy();
  });
});
