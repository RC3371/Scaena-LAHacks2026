import { createBrowserRouter } from "react-router-dom";
import { Layout } from "./Layout";
import { Dashboard } from "./Dashboard";
import { MarketInsights } from "./MarketInsights";
import { Outreach } from "./Outreach";
import { Analytics } from "./Analytics";
import { Pipeline } from "./Pipeline";
import { Onboarding } from "./Onboarding";

export const router = createBrowserRouter([
  {
    path: "/onboarding",
    element: <Onboarding />,
  },
  {
    path: "/",
    element: <Layout />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: "insights", element: <MarketInsights /> },
      { path: "outreach", element: <Outreach /> },
      { path: "analytics", element: <Analytics /> },
      { path: "pipeline", element: <Pipeline /> },
    ],
  },
]);
