import { ThreadList } from '../../components/ThreadList';
import { getViewThreads } from '../../lib/api';

export default async function DonePage() {
  const threads = await getViewThreads('done');

  return (
    <section>
      <h1>Done</h1>
      <ThreadList items={threads} />
    </section>
  );
}
