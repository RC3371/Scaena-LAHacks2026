import { createBrowserRouter } from "react-router";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { MarketInsights } from "./pages/MarketInsights";
import { Outreach } from "./pages/Outreach";
import { Pipeline } from "./pages/Pipeline";
import { Analytics } from "./pages/Analytics";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Layout,
    children: [
      { index: true, Component: Dashboard },
      { path: "insights", Component: MarketInsights },
      { path: "outreach", Component: Outreach },
      { path: "pipeline", Component: Pipeline },
      { path: "analytics", Component: Analytics },
    ],
  },
]);
