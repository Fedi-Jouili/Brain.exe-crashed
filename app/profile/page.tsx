import { Header } from "@/components/layout/header"
import { ProfileSetupWizard } from "@/components/profile/profile-setup-wizard"

export default function ProfilePage() {
  return (
    <div className="flex min-h-screen flex-col bg-background">
      <Header />
      <main className="flex-1">
        <div className="mx-auto max-w-2xl px-4 py-12 sm:px-6 lg:px-8">
          <ProfileSetupWizard />
        </div>
      </main>
    </div>
  )
}
