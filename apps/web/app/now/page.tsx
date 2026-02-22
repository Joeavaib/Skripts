import { ThreadList } from '../../components/ThreadList';
import { getViewThreads } from '../../lib/api';

export default async function NowPage() {
  const threads = await getViewThreads('now');

  return (
    <section>
      <h1>Now</h1>
      <ThreadList items={threads} />
    </section>
  );
}
