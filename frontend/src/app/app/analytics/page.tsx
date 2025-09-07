import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Icon } from "@/components/ui/icon"

export default function AnalyticsPage() {
  const metrics = [
    { title: "Total Revenue", value: "$48,230", change: "+12.5%", trend: "up" },
    { title: "Customer Acquisition", value: "324", change: "+8.2%", trend: "up" },
    { title: "Campaign Performance", value: "87%", change: "+3.1%", trend: "up" },
    { title: "Customer Retention", value: "92%", change: "-1.2%", trend: "down" },
  ]

  return (
    <div className="flex flex-col min-h-screen bg-[#f9f9f9]">
      <main className="flex-grow container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-[#1a1a1a]">Analytics</h1>
          <p className="mt-2 text-[#666666]">Track your restaurant's performance and marketing effectiveness.</p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
          {metrics.map((metric, index) => (
            <Card key={index}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">{metric.title}</CardTitle>
                <Icon
                  name={metric.trend === "up" ? "trending_up" : "trending_down"}
                  className={`h-4 w-4 ${metric.trend === "up" ? "text-green-600" : "text-red-600"}`}
                />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{metric.value}</div>
                <p className={`text-xs ${metric.trend === "up" ? "text-green-600" : "text-red-600"}`}>
                  {metric.change} from last month
                </p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Campaign Performance</CardTitle>
              <CardDescription>Your top performing campaigns this month</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Summer Special Promotion</p>
                    <p className="text-sm text-muted-foreground">4.2% conversion rate</p>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">$3,240</p>
                    <p className="text-sm text-green-600">+18%</p>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Weekend Brunch Campaign</p>
                    <p className="text-sm text-muted-foreground">3.8% conversion rate</p>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">$5,680</p>
                    <p className="text-sm text-green-600">+12%</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Customer Insights</CardTitle>
              <CardDescription>Understanding your customer base</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Repeat Customers</span>
                  <span className="font-medium">68%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Average Order Value</span>
                  <span className="font-medium">$42.50</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Customer Satisfaction</span>
                  <span className="font-medium">4.7/5</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
}
