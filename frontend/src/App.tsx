import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { UploadPage } from './pages/UploadPage';
import { InvoiceListPage } from './pages/InvoiceListPage';
import { InvoiceDetailPage } from './pages/InvoiceDetailPage';
import { ApprovalsPage } from './pages/ApprovalsPage';
import { FeedbackPage } from './pages/FeedbackPage';
import { PromptsPage } from './pages/PromptsPage';
import { useCurrentUser } from './hooks/useCurrentUser';

function App() {
  const { users, currentUser, switchUser } = useCurrentUser();

  return (
    <BrowserRouter>
      <Routes>
        <Route
          element={
            <Layout users={users} currentUser={currentUser} onSwitchUser={switchUser} />
          }
        >
          <Route path="/" element={<DashboardPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/invoices" element={<InvoiceListPage />} />
          <Route path="/invoices/:id" element={<InvoiceDetailPage currentUser={currentUser} />} />
          <Route path="/approvals" element={<ApprovalsPage />} />
          <Route path="/feedback" element={<FeedbackPage currentUser={currentUser} />} />
          <Route path="/prompts" element={<PromptsPage currentUser={currentUser} />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
