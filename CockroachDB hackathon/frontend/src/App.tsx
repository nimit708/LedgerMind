import { Authenticator } from "@aws-amplify/ui-react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "@aws-amplify/ui-react/styles.css";

import { Dashboard } from "./pages/Dashboard";
import { AgentChat } from "./pages/AgentChat";
import { Approvals } from "./pages/Approvals";
import { Payments } from "./pages/Payments";
import { Forecast } from "./pages/Forecast";
import { Audit } from "./pages/Audit";
import { Layout } from "./components/Layout";

const queryClient = new QueryClient();

function AppContent({ signOut, user }: { signOut?: () => void; user?: any }) {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout user={user} onSignOut={signOut}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/agent" element={<AgentChat />} />
            <Route path="/approvals" element={<Approvals />} />
            <Route path="/payments" element={<Payments />} />
            <Route path="/forecast" element={<Forecast />} />
            <Route path="/audit" element={<Audit />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

function App() {
  const hasAuth = import.meta.env.VITE_COGNITO_USER_POOL_ID && import.meta.env.VITE_COGNITO_CLIENT_ID;

  if (!hasAuth) {
    return <AppContent />;
  }

  return (
    <Authenticator
      signUpAttributes={["email"]}
      loginMechanisms={["email"]}
      hideSignUp={false}
    >
      {({ signOut, user }) => <AppContent signOut={signOut} user={user} />}
    </Authenticator>
  );
}

export default App;
