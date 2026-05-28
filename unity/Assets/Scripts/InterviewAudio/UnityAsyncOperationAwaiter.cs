using System;
using System.Runtime.CompilerServices;
using UnityEngine;

namespace TFG.InterviewAudio
{
    public static class UnityAsyncOperationAwaiter
    {
        public static AsyncOperationAwaiter GetAwaiter(this AsyncOperation operation)
        {
            return new AsyncOperationAwaiter(operation);
        }
    }

    public sealed class AsyncOperationAwaiter : INotifyCompletion
    {
        private readonly AsyncOperation _operation;

        public AsyncOperationAwaiter(AsyncOperation operation)
        {
            _operation = operation;
        }

        public bool IsCompleted => _operation.isDone;

        public void OnCompleted(Action continuation)
        {
            _operation.completed += _ => continuation();
        }

        public void GetResult()
        {
        }
    }
}
