/**
 * @Author: Bi Ying
 * @Date:   2024-07-24 15:00:13
 * @Last Modified by:   Bi Ying
 * @Last Modified time: 2024-07-24 15:00:28
 */
'use strict';
export const chatModelOptions = [
  {
    label: "OpenAI",
    value: "OpenAI",
    children: [
      {
        label: "gpt-35-turbo",
        value: "gpt-35-turbo",
      },
      {
        label: "gpt-4",
        value: "gpt-4",
      },
      {
        label: "gpt-4o",
        value: "gpt-4o",
      },
    ]
  },
  {
    label: "MiniMax",
    value: "MiniMax",
    children: [
      {
        label: "abab5.5-chat",
        value: "abab5.5-chat",
      },
      {
        label: "abab6-chat",
        value: "abab6-chat",
      },
      {
        label: "abab6.5s-chat",
        value: "abab6.5s-chat",
      },
    ]
  },
  {
    label: "ZhiPuAI",
    value: "ZhiPuAI",
    children: [
      {
        label: "glm-3-turbo",
        value: "glm-3-turbo",
      },
      {
        label: "glm-4",
        value: "glm-4",
      },
      {
        label: "glm-4-0520",
        value: "glm-4-0520",
      },
      {
        label: "glm-4-air",
        value: "glm-4-air",
      },
      {
        label: "glm-4-airx",
        value: "glm-4-airx",
      },
      {
        label: "glm-4-flash",
        value: "glm-4-flash",
      },
    ]
  },
  {
    label: "Qwen",
    value: "Qwen",
    children: [
      {
        label: "qwen1.5-7b-chat",
        value: "qwen1.5-7b-chat",
      },
      {
        label: "qwen1.5-14b-chat",
        value: "qwen1.5-14b-chat",
      },
      {
        label: "qwen1.5-32b-chat",
        value: "qwen1.5-32b-chat",
      },
      {
        label: "qwen1.5-72b-chat",
        value: "qwen1.5-72b-chat",
      },
      {
        label: "qwen1.5-110b-chat",
        value: "qwen1.5-110b-chat",
      },
      {
        label: "qwen2-72b-instruct",
        value: "qwen2-72b-instruct",
      },
    ]
  },
  {
    label: "Moonshot",
    value: "Moonshot",
    children: [
      {
        label: "moonshot-v1-8k",
        value: "moonshot-v1-8k",
      },
      {
        label: "moonshot-v1-32k",
        value: "moonshot-v1-32k",
      },
      {
        label: "moonshot-v1-128k",
        value: "moonshot-v1-128k",
      },
    ]
  },
  {
    label: "Anthropic",
    value: "Anthropic",
    children: [
      {
        label: "claude-3-haiku",
        value: "claude-3-haiku-20240307",
      },
      {
        label: "claude-3-sonnet",
        value: "claude-3-sonnet-20240229",
      },
      {
        label: "claude-3-opus",
        value: "claude-3-opus-20240229",
      },
      {
        label: "claude-3-5-sonnet",
        value: "claude-3-5-sonnet-20240620",
      },
    ]
  },
  {
    label: "Mistral",
    value: "Mistral",
    children: [
      {
        label: "mixtral-8x7b",
        value: "mixtral-8x7b",
      },
      {
        label: "mistral-small",
        value: "mistral-small",
      },
      {
        label: "mistral-medium",
        value: "mistral-medium",
      },
      {
        label: "mistral-large",
        value: "mistral-large",
      },
    ]
  },
  {
    label: "DeepSeek",
    value: "DeepSeek",
    children: [
      {
        label: "deepseek-chat",
        value: "deepseek-chat",
      },
      {
        label: "deepseek-coder",
        value: "deepseek-coder",
      },
    ]
  },
  {
    label: "Yi",
    value: "Yi",
    children: [
      {
        label: "yi-large",
        value: "yi-large",
      },
      {
        label: "yi-large-turbo",
        value: "yi-large-turbo",
      },
      {
        label: "yi-medium",
        value: "yi-medium",
      },
      {
        label: "yi-medium-200k",
        value: "yi-medium-200k",
      },
      {
        label: "yi-spark",
        value: "yi-spark",
      },
    ]
  },
]

const flattenModelOptions = (options, showProvider = true) => {
  const flattenedOptions = [];

  options.forEach(option => {
    if (option.children && option.children.length > 0) {
      option.children.forEach(child => {
        flattenedOptions.push({
          label: showProvider ? `${option.label}/${child.label}` : child.label,
          value: showProvider ? `${option.value}/${child.value}` : child.value,
        });
      });
    }
  });

  return flattenedOptions;
}

export const flattenedChatModelOptions = flattenModelOptions(chatModelOptions)
