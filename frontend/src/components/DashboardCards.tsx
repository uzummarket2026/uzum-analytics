export default function DashboardCards() {
  const stats = [
    { name: 'Total Revenue', value: '$45,231.89', change: '+20.1%' },
    { name: 'Active Orders', value: '356', change: '+5.4%' },
    { name: 'Total Products', value: '12', change: '0%' },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {stats.map((stat) => (
        <div key={stat.name} className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm font-medium text-gray-500">{stat.name}</h3>
          <div className="mt-2 flex items-baseline">
            <p className="text-3xl font-semibold text-gray-900">{stat.value}</p>
            <p className="ml-2 flex items-baseline text-sm font-semibold text-green-600">
              {stat.change}
            </p>
          </div>
        </div>
      ))}
    </div>
  )
}
