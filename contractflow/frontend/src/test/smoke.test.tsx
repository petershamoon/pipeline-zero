import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { LoginPage } from "../pages/LoginPage";

describe("LoginPage", () => {
  it("renders the login heading", () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>,
    );

    expect(screen.getByText("ContractFlow Login")).toBeInTheDocument();
  });
});
