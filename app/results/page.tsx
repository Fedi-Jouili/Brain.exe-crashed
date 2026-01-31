import { Header } from "@/components/layout/header"
import { Footer } from "@/components/layout/footer"
import { ResultsView } from "@/components/results/results-view"

export default function ResultsPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1 bg-background">
        <ResultsView />
      </main>
      <Footer />
    </div>
  )
}
