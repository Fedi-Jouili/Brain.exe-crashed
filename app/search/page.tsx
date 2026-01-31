import { Header } from "@/components/layout/header"
import { Footer } from "@/components/layout/footer"
import { SearchInterface } from "@/components/search/search-interface"

export default function SearchPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1 bg-background">
        <SearchInterface />
      </main>
      <Footer />
    </div>
  )
}
