import { SessionFlow } from '../../components/SessionFlow';
import { getViewThreads } from '../../lib/api';

export default async function UncheckedPage() {
  const threads = await getViewThreads('unchecked');

  return (
    <section>
      <h1>Unchecked</h1>
      <p>Process unchecked until empty.</p>
      <SessionFlow initialThreads={threads} />
    </section>
  );
}
