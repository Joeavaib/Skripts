import { ThreadList } from '../../components/ThreadList';
import { getViewThreads } from '../../lib/api';

export default async function LaterPage() {
  const threads = await getViewThreads('later');

  return (
    <section>
      <h1>Later</h1>
      <ThreadList items={threads} />
    </section>
  );
}
