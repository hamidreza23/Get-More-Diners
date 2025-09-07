export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-background">
      {/* Auth Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 h-16 flex items-center">
          <a href="/" className="flex items-center space-x-2">
            <span className="text-2xl font-bold brand-text-gradient">
              Get More Diners
            </span>
          </a>
        </div>
      </header>

      {/* Auth Content */}
      <main className="flex-1">
        {children}
      </main>

      {/* Auth Footer */}
      <footer className="border-t py-6">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          © 2024 Get More Diners. All rights reserved.
        </div>
      </footer>
    </div>
  )
}
