export default function Home() {
  return (
    <div>
      <h1 className="text-4xl font-bold mb-4">Welcome to the AstroPropose Framework</h1>
      <p className="text-lg">
        This is a general and customizable framework for astronomical observing proposals.
      </p>
      <p className="mt-4">
        Navigate to the <a href="/admin/workflows" className="text-blue-500 hover:underline">Workflow Editor</a> to see the core feature in action.
      </p>
    </div>
  )
}
